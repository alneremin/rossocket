
import json
from geometry_msgs.msg import Twist

def get_data_class(name):

    classes = {
        'geometry_msgs/Twist': Twist
    }

    return classes[name] if name in classes.keys() else None


def _Twist(data):

    twist = Twist()
    twist.linear.x = try_get(data,'linear_x', float, 0)
    twist.linear.y = try_get(data,'linear_y', float, 0)
    twist.linear.z = try_get(data,'linear_z', float, 0)

    twist.angular.x = try_get(data,'angular_x', float, 0)
    twist.angular.y = try_get(data,'angular_y', float, 0)
    twist.angular.z = try_get(data,'angular_z', float, 0)

    return twist


def try_get(_dict, prop, cast, _default):
    if prop in _dict.keys():
        return cast(_dict[prop])
    else:
        return _default


def process_class_data(cls_name, data):
    
    obj_data = json.loads(data)

    classes = {
        'geometry_msgs/Twist': _Twist
    }

    return classes[cls_name](obj_data) if cls_name in classes.keys() else None
