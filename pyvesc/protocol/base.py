from construct import *
from pprint import pprint

class VESCMessage(type):
    """ Metaclass for VESC messages.

    This is the metaclass for any VESC message classes. A VESC message class must then declare 2-3 static attributes:
    id: unsigned integer which is the identification number for messages of this class
    fields: a construct.Struct - see: https://construct.readthedocs.io
    scalars: a dictionary of field names to scalars to be applied upon unpack
    """
   
    #a list of messages we know about to avoid duplicates
    _msg_registry = {}
    
    #some standard parts of the packet we will use later
    _id_fmt = 'msg_id' / Byte
    _can_id_fmt = Struct('comm_fwd_can' / Const(33, Byte), 'source_can_id' / Byte)

    def __init__(cls, name, bases, clsdict):
        cls.can_id = None
        msg_id = clsdict['id']

        #some classes might not have this set
        if not hasattr(cls, 'scalars'):
            cls.scalars = {}

        # make sure that message classes are final
        for klass in bases:
            if isinstance(klass, VESCMessage):
                raise TypeError("VESC messages cannot be inherited.")

        # check for duplicate id
        if msg_id in VESCMessage._msg_registry:
            raise TypeError("ID conflict with %s" % str(VESCMessage._msg_registry[msg_id]))
        else:
            VESCMessage._msg_registry[msg_id] = cls

        super(VESCMessage, cls).__init__(name, bases, clsdict)

    def __call__(cls, *args, **kwargs):
        instance = super(VESCMessage, cls).__call__()
        if 'can_id' in kwargs:
            instance.can_id = kwargs['can_id']
        else:
            instance.can_id = None
        if args:
            if len(args) != len(cls.fields.subcons):
                raise AttributeError("Expected %u arguments, received %u" % (len(cls.fields), len(args)))
            for subcon, value in zip(cls.fields.subcons, args):
                setattr(instance, subcon.name, value)
        return instance

    @staticmethod
    def msg_type(id):
        return VESCMessage._msg_registry[id]

    @staticmethod
    def unpack(msg_bytes):

        print('unpack')
        pprint(msg_bytes)

        #first byte is our message id
        msg_id = construct.Byte.parse(msg_bytes)
        
        #use the magic factory to make our VESCMessage class
        msg_type = VESCMessage.msg_type(*msg_id)
        
        #parse our data, skipping that first byte
        data = msg_type.fields.parse(msg_bytes[1:])
        for k, field in enumerate(data):
            try:
                #some of the float values are multiplied by a scalar and need to be converted back
                if k in msg_type.scalars:
                    data[k] = data[k] / msg_type.scalars[k]
            except (TypeError, IndexError) as e:
                print("Error ecountered on field " + msg_type.fields[k][0])
                print(e)

        #create a new object and return it?
        msg = msg_type(*data)

        return msg


    @staticmethod
    def pack(instance, header_only=None):
        fmt = Struct()
        values = {}

        #can id stuff has a special format
        if instance.can_id is not None:
            fmt += VESCMessage._can_id_fmt
            values['source_can_id'] = instance.can_id
        
        #now our message id.
        fmt += VESCMessage._id_fmt
        values['msg_id'] = int(instance.id)

        #are we sending data along too?
        if header_only is None:
            #add in our message specific fields
            fmt += instance.fields

            #loop through our data...
            for subcon in instance.fields.subcons:
                if subcon.name in instance.scalars:
                    values[subcon.name] = int(getattr(instance, subcon.name) * instance.scalars[subcon.name])
                else:
                    values[subcon.name] = getattr(instance, subcon.name)
        
        print('pack')
        pprint(fmt)
        pprint(values)
        pprint(fmt.build(values))
        
        return fmt.build(values)
